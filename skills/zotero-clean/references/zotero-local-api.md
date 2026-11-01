# Zotero local API notes

The supported interface for this workflow is the local Zotero HTTP API. Use the user library base URL from the authorization cache and send these headers:

- `Zotero-API-Version: 3`
- `Zotero-API-Key: <local key>`
- `Zotero-Server-ID: <server id>`
- `Content-Type: application/json` for writes

Read an item with `GET /items/{itemKey}`. Update only collection membership with a versioned `PATCH /items/{itemKey}` payload:

```json
{
  "key": "ITEMKEY",
  "version": 123,
  "collections": ["DESTINATION_KEY"]
}
```

The item key and version come from the immediately preceding GET. A version conflict is a stop condition: refetch, reassess the plan, and do not overwrite a concurrent change. Collection names and counts come from `GET /collections` and collection contents from `GET /collections/{collectionKey}/items`.

The local key is a credential. Keep it outside Git, logs, manifests, and generated indexes.

If the key is absent or rejected, stop the workflow and request a researcher-authorized key refresh. Do not switch to desktop automation or direct SQLite/database access.
