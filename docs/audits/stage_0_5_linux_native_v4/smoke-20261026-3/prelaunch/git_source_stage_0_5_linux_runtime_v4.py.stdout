"""Static Linux runtime closure and exact capsule policy preparation."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import sysconfig

sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_0_5_native_capsule_v4 import canonical,sha,require


def resolve_dependency(needed,rpaths,libraries,bound_files):
    candidates=[(folder/needed).resolve() for folder in rpaths if (folder/needed).is_file()]
    if candidates:return candidates[0]
    if needed in libraries:return libraries[needed]
    # auditwheel libraries can inherit an ancestor ELF's DT_RPATH. Include an
    # unambiguous, already hashed wheel member in the static closure; the native
    # smoke must still prove that the real loader resolves the dependency.
    bundled={Path(n) for n in bound_files if Path(n).name==needed}
    require(len(bundled)==1,"unresolved_or_ambiguous_ELF_dependency:"+needed)
    return bundled.pop()


def runtime_manifest(installation_root):
    import sumo
    root=Path(installation_root).resolve();env=Path(sys.prefix).resolve()
    require(env==root/"env","wrong_project_interpreter")
    require(not Path(sys.executable).is_symlink(),"copied_project_interpreter_required")
    installation=json.loads((root/"installation_record.json").read_bytes())
    require(installation["pins"]["eclipse-sumo"]=="1.26.0","wrong_installed_release")
    for r in installation["wheels"]:
        require(sha(root/"wheels"/r["filename"])==r["sha256"],"installed_wheel_archive_drift")
        require(importlib.metadata.version(r["package"])==r["version"],"installed_package_version_drift:"+r["package"])
    home=Path(sumo.__file__).resolve().parent;binary=home/"bin/sumo";tools=home/"tools"
    require(binary.is_file() and (tools/"traci/__init__.py").is_file(),"wheel_SUMO_layout_unavailable")
    stdlib=Path(sysconfig.get_path("stdlib")).resolve()
    files={};roots=[env,stdlib]
    for base in roots:
        for directory,children,names in os.walk(base,followlinks=False):
            if base==stdlib:children[:]=[n for n in children if n not in {"site-packages"}]
            for n in names:
                p=(Path(directory)/n).resolve()
                if p.is_file():files[str(p)]=sha(p)
    cache=subprocess.check_output(["/sbin/ldconfig","-p"],text=True)
    libraries={}
    for line in cache.splitlines():
        m=re.match(r"\s*(\S+).*=> (\S+)",line)
        if m:libraries[m[1]]=Path(m[2]).resolve()
    queue=[]
    for name in files:
        with open(name,"rb") as f:
            if f.read(4)==b"\x7fELF":queue.append(Path(name))
    inspected=set();loaders=set()
    while queue:
        p=queue.pop()
        if p in inspected:continue
        inspected.add(p);files[str(p)]=sha(p)
        dynamic=subprocess.check_output(["/usr/bin/readelf","-d",str(p)],text=True,stderr=subprocess.DEVNULL)
        rpaths=[]
        for value in re.findall(r"\((?:RUNPATH|RPATH)\).*\[(.*?)\]",dynamic):
            rpaths += [Path(t.replace("${ORIGIN}",str(p.parent)).replace("$ORIGIN",str(p.parent))) for t in value.split(":") if t]
        for needed in re.findall(r"\(NEEDED\).*\[(.*?)\]",dynamic):
            target=resolve_dependency(needed,rpaths,libraries,files)
            queue.append(target)
        program=subprocess.check_output(["/usr/bin/readelf","-l",str(p)],text=True,stderr=subprocess.DEVNULL)
        for loader in re.findall(r"Requesting program interpreter: (.*?)\]",program):
            real=Path(loader).resolve();loaders.add(str(real));queue.append(real)
    configs=[]
    for name in ["/etc/ld.so.cache","/etc/hosts","/etc/nsswitch.conf","/etc/gai.conf","/etc/resolv.conf","/etc/localtime"]:
        p=Path(name).resolve()
        if p.is_file():files[str(p)]=sha(p);configs.append(str(p))
    protocol=int(re.search(r"TRACI_VERSION\s*=\s*(\d+)",(tools/"traci/constants.py").read_text())[1])
    external=[n for n in files if not any(Path(n).is_relative_to(r) for r in roots)]
    return dict(schema="aad.linux-runtime.v4",python_executable=sys.executable,python_version=sys.version,
        python_sha256=sha(sys.executable),sumo_home=str(home),sumo_binary=str(binary),sumo_sha256=sha(binary),
        sumo_release="1.26.0",traci_tools_root=str(tools),traci_init_sha256=sha(tools/"traci/__init__.py"),
        traci_protocol=protocol,tripinfo_schema=str(home/"data/xsd/tripinfo_file.xsd"),
        installation_record_sha256=sha(root/"installation_record.json"),wheel_records=installation["wheels"],
        packages=installation["pins"],files=files,readonly_paths=[str(r) for r in roots]+external,
        executables=[sys.executable,str(binary)]+sorted(loaders),kernel=os.uname().release,
        OS_release=Path("/etc/os-release").read_text(),runtime_root=str(root))


def check_runtime(manifest):
    require(manifest["sumo_release"]=="1.26.0","runtime_release_mismatch")
    for n,expected in manifest["files"].items():require(sha(n)==expected,"runtime_dependency_drift:"+n)
    require(sha(manifest["sumo_binary"])==manifest["sumo_sha256"],"runtime_binary_drift")
    require(sha(manifest["python_executable"])==manifest["python_sha256"],"runtime_interpreter_drift")
    return True


def make_policy(capsule,runtime,runtime_path,source_files,inputs,run,*,accepted_build,capability_record):
    from stage_0_5_linux_isolation import policy_bytes
    capsule=Path(capsule).absolute();capsule.mkdir(exist_ok=False)
    # Python's module finder needs READ_DIR as well as exact source-file reads.
    # Give it a dedicated immutable closure, never the mixed staging directory.
    source_dir=capsule/"controller_sources";source_dir.mkdir()
    copies={}
    for name,source in source_files.items():
        require(Path(name).name==name,"controller_source_name")
        target=source_dir/name
        with target.open("xb") as f:f.write(Path(source).read_bytes())
        copies[name]=str(target)
    source_files=copies
    files=dict(runtime["files"])
    for n in list(source_files.values())+list(inputs.values())+[str(runtime_path),str(capability_record)]:files[n]=sha(n)
    limits=run["single_attempt_limits"]
    policy=dict(purpose="stage0.5-production-v4",capsule=str(capsule),scratch=str(capsule/"scratch"),archive=str(capsule/"archive"),
        argv=[runtime["python_executable"],"-I","-B",source_files["stage_0_5_linux_controller_v4.py"]],
        executables=runtime["executables"],file_sha256=files,readonly_paths=runtime["readonly_paths"]+[str(source_dir)],
        kernel_readonly=["/proc","/sys/fs/cgroup"],inputs=inputs,
        memory_bytes=limits["process_tree_rss_bytes"],output_bytes=limits["task_output_bytes"],tasks=32,wall_s=limits["per_attempt_wall_s"],
        environment=dict(PATH=str(Path(runtime["sumo_binary"]).parent)+":/usr/bin",SUMO_HOME=runtime["sumo_home"],
            OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",LANG="C.UTF-8",LC_ALL="C.UTF-8"),
        host_namespaces={n:os.readlink("/proc/self/ns/"+n) for n in ["user","mnt","pid","net","ipc"]},
        binding=dict(runtime_manifest_path=str(runtime_path),runtime_manifest_sha256=sha(runtime_path),source_files=source_files,
            capability_record_path=str(capability_record),capability_record_sha256=sha(capability_record),
            source_sha256={n:sha(p) for n,p in source_files.items()},accepted_build=accepted_build))
    path=capsule/"policy.json"
    with path.open("xb") as f:f.write(policy_bytes(policy))
    return path,policy


if __name__=="__main__":
    sys.stdout.buffer.write(canonical(runtime_manifest(sys.argv[1]))+b"\n")
