"""Project-only pinned wheel installation. No SUMO/netconvert process is run."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import venv
import zipfile

PINS={"pip":"25.2","eclipse-sumo":"1.26.0","numpy":"2.3.2","pandas":"2.2.3",
      "pyarrow":"25.0.1","psutil":"7.2.2","python-dateutil":"2.9.0.post0",
      "pytz":"2025.2","tzdata":"2025.2","six":"1.17.0","pytest":"8.4.1",
      "packaging":"24.2","pluggy":"1.5.0","iniconfig":"2.1.0","pygments":"2.19.1"}
SUMO_WHEEL="eclipse_sumo-1.26.0-py3-none-manylinux_2_28_x86_64.whl"
SUMO_SHA="34c7adc99d61f5c93a4c9bfa95870cd78a67f3eaa5b10ce224163a56ab0685a4"
AUTHORIZED_ROOT=Path("/home/shen/AAD/code/runtime/stage_0_5_sumo126_v4_r2")
ALLOWED_DOWNLOAD_HOSTS={"pypi.org","files.pythonhosted.org"}
MAX_WHEEL_BYTES=512*1024**2
MAX_TOTAL_WHEEL_BYTES=2*1024**3


class RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def validate_url(url):
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS or parsed.username or parsed.password:
        raise ValueError("download_url_outside_pypi_allowlist")
    return url


OPENER=urllib.request.build_opener(RestrictedRedirectHandler())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda:f.read(1024*1024),b""):h.update(data)
    return h.hexdigest()


def metadata(name,version):
    url=validate_url("https://pypi.org/pypi/"+name+"/"+version+"/json")
    with OPENER.open(url,timeout=60) as f:
        data=f.read(8*1024**2+1)
    if len(data)>8*1024**2:raise ValueError("pypi_metadata_too_large")
    result=json.loads(data)
    if result.get("info",{}).get("version")!=version or result.get("info",{}).get("name","").lower().replace("_","-")!=name.lower().replace("_","-"):
        raise ValueError("pypi_metadata_identity_mismatch:"+name)
    return result


def download(folder,item):
    validate_url(item["url"])
    expected=item.get("digests",{}).get("sha256")
    if not isinstance(expected,str) or len(expected)!=64:raise ValueError("missing_wheel_sha256")
    declared=item.get("size")
    if not isinstance(declared,int) or declared<1 or declared>MAX_WHEEL_BYTES:raise ValueError("wheel_size_outside_limit")
    filename=item["filename"]
    if Path(filename).name!=filename or not filename.endswith(".whl"):raise ValueError("unsafe_wheel_filename")
    path=folder/filename
    if path.exists():
        if path.stat().st_size==declared and sha(path)==expected:return path
        interrupted=folder.parent/"interrupted";interrupted.mkdir(exist_ok=True)
        retained=interrupted/(path.name+"."+str(time.time_ns()))
        path.rename(retained)
    total=0
    with path.open("xb") as out,OPENER.open(item["url"],timeout=120) as remote:
        if remote.geturl()!=item["url"]:validate_url(remote.geturl())
        header=remote.headers.get("Content-Length")
        if header is not None and int(header)!=declared:raise ValueError("wheel_content_length_mismatch")
        while True:
            block=remote.read(1024*1024)
            if not block:break
            total+=len(block)
            if total>declared or total>MAX_WHEEL_BYTES:raise ValueError("wheel_download_exceeded_declared_size")
            out.write(block)
    if total!=declared or sha(path)!=expected:
        raise ValueError("download_hash_mismatch:"+path.name)
    return path


def prepare(root,*,resume_interrupted=False):
    root=Path(root).absolute()
    if root!=AUTHORIZED_ROOT or any(p.is_symlink() for p in [root,*root.parents]):raise ValueError("exact_project_runtime_directory_required")
    if root.exists() and not resume_interrupted:raise ValueError("new_project_runtime_directory_required")
    if resume_interrupted and ((root/"installation_record.json").exists() or (root/"env").exists()):
        raise ValueError("resume_only_interrupted_download_not_existing_install")
    if resume_interrupted and root.exists():
        allowed={"wheels","tmp","download_interruption_"}
        for child in root.iterdir():
            if child.name not in allowed and not child.name.startswith("download_interruption_"):
                raise ValueError("unexpected_existing_runtime_path:"+child.name)
        for child in (root/"wheels").iterdir() if (root/"wheels").exists() else []:
            if not child.is_file() or child.is_symlink():raise ValueError("unexpected_existing_wheel_path")
    if shutil.disk_usage("/home/shen/AAD").free<6*1024**3:raise RuntimeError("runtime_disk_headroom_insufficient")
    root.mkdir(parents=True,exist_ok=resume_interrupted);wheels=root/"wheels";wheels.mkdir(exist_ok=resume_interrupted)
    (root/"tmp").mkdir(exist_ok=resume_interrupted)
    if resume_interrupted:
        (root/("download_interruption_"+str(time.time_ns())+".json")).write_text(json.dumps(dict(
            reason="Prior tool process ended before installation record; explicit download recovery",
            files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in wheels.iterdir() if p.is_file()})))
    install_environment=dict(PATH="/usr/bin:/bin",HOME=str(root/"tmp"),TMPDIR=str(root/"tmp"),
        PIP_CONFIG_FILE="/dev/null",PIP_DISABLE_PIP_VERSION_CHECK="1",PIP_NO_CACHE_DIR="1",PYTHONDONTWRITEBYTECODE="1")
    record=dict(working_directory=os.getcwd(),runtime_root=str(root),pins=PINS,wheels=[],commands=[],download_limits=dict(per_wheel_bytes=MAX_WHEEL_BYTES,total_bytes=MAX_TOTAL_WHEEL_BYTES,hosts=sorted(ALLOWED_DOWNLOAD_HOSTS)),
                SUMO_launches=0,netconvert_launches=0,system_packages_changed=False)
    try:
        pip_data=metadata("pip",PINS["pip"])
        pip_item=next(x for x in pip_data["urls"] if x["filename"].endswith("-py3-none-any.whl"))
        pip_path=download(wheels,pip_item)
        sys.path.insert(0,str(pip_path))
        from pip._vendor.packaging.tags import sys_tags
        from pip._vendor.packaging.utils import parse_wheel_filename
        tags={v:i for i,v in enumerate(sys_tags())}
        total_wheel_bytes=0;total_unpacked_bytes=0
        for name,version in PINS.items():
            data=pip_data if name=="pip" else metadata(name,version)
            candidates=[]
            for item in data["urls"]:
                if not item["filename"].endswith(".whl"):continue
                _,_,_,wheel_tags=parse_wheel_filename(item["filename"])
                overlap=wheel_tags&set(tags)
                if overlap:candidates.append((min(tags[t] for t in overlap),item))
            if not candidates:raise ValueError("no_compatible_fixed_wheel:"+name)
            item=min(candidates,key=lambda x:x[0])[1]
            if name=="eclipse-sumo" and (item["filename"]!=SUMO_WHEEL or item["digests"]["sha256"]!=SUMO_SHA):
                raise ValueError("authorized_SUMO_wheel_mismatch")
            total_wheel_bytes+=item.get("size",MAX_TOTAL_WHEEL_BYTES+1)
            if total_wheel_bytes>MAX_TOTAL_WHEEL_BYTES:raise ValueError("fixed_wheel_set_exceeds_total_download_limit")
            path=pip_path if name=="pip" else download(wheels,item)
            with zipfile.ZipFile(path) as z:
                total_unpacked_bytes+=sum(i.file_size for i in z.infolist())
                if total_unpacked_bytes>4*1024**3:raise ValueError("wheel_set_unpacked_size_exceeds_limit")
                if any(Path(n).is_absolute() or ".." in Path(n).parts for n in z.namelist()):
                    raise ValueError("unsafe_wheel_members")
            record["wheels"].append(dict(package=name,version=version,filename=path.name,url=item["url"],sha256=sha(path),bytes=path.stat().st_size))
            print("VERIFIED_WHEEL="+path.name,flush=True)
        requirements=root/"requirements.lock"
        with requirements.open("x") as handle:handle.write("\n".join(r["package"]+"=="+r["version"]+" --hash=sha256:"+r["sha256"] for r in record["wheels"])+"\n")
        env=root/"env";venv.EnvBuilder(with_pip=False,symlinks=False).create(env)
        python=env/"bin/python3"
        bootstrap="import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('pip',run_name='__main__')"
        argv=[str(python),"-I","-B","-c",bootstrap,str(pip_path),"install","--no-index","--no-deps","--no-compile","--require-hashes","--find-links",str(wheels),"-r",str(requirements)]
        with (root/"install.log").open("xb") as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,env=install_environment,timeout=300)
        record["commands"].append(dict(argv=argv,exit_code=r.returncode,log_sha256=sha(root/"install.log")))
        if r.returncode:raise RuntimeError("pinned_install_failed")
        argv=[str(python),"-I","-B","-m","pip","check"]
        r=subprocess.run(argv,capture_output=True,env=install_environment,timeout=60)
        with (root/"pip_check.log").open("xb") as handle:handle.write(r.stdout+r.stderr)
        record["commands"].append(dict(argv=argv,exit_code=r.returncode,log_sha256=sha(root/"pip_check.log")))
        if r.returncode:raise RuntimeError("fixed_dependency_incompatibility")
        probe="import importlib,json,pathlib,sys; names=['numpy','pandas','pyarrow','psutil']; modules={n:importlib.import_module(n) for n in names}; import sumo; print(json.dumps({'python':sys.version,'executable':sys.executable,'sumo_module':sumo.__file__,'sumo_home':str(pathlib.Path(sumo.__file__).parent),'modules':{n:{'version':m.__version__,'file':m.__file__} for n,m in modules.items()}}))"
        r=subprocess.run([str(python),"-I","-B","-c",probe],capture_output=True,env=install_environment,timeout=60)
        with (root/"import_probe.log").open("xb") as handle:handle.write(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError("fixed_runtime_import_failed")
        record["installed"]=json.loads(r.stdout);record["python_sha256"]=sha(python)
        record["status"]="Installed pinned project runtime; no SUMO process executed"
    except BaseException as error:
        record["status"]="Failed, retained without retry";record["failure"]=repr(error);raise
    finally:
        with (root/"installation_record.json").open("x") as f:json.dump(record,f,indent=2)
    print(json.dumps(record["installed"],sort_keys=True),flush=True)
    print("INSTALLATION_RECORD="+str(root/"installation_record.json"),flush=True)


if __name__=="__main__":
    prepare(sys.argv[1],resume_interrupted=sys.argv[2:]==["--resume-interrupted"])
