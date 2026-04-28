# Vercel Deployment Notes

This repo is prepared to deploy the Next.js frontend and FastAPI backend together on Vercel.

## What was added

- `api/index.py` exposes the FastAPI `app` as a Vercel Python Function.
- `vercel.json` routes `/api/v1/*` requests to that Python Function.
- Root `requirements.txt` lets Vercel install backend Python dependencies.
- The frontend defaults to `/api/v1` when `NEXT_PUBLIC_API_URL` is not set.

## Required Vercel environment variables

For stable verification across cold starts, set these in Vercel:

- `RSA_PRIVATE_KEY_B64`
- `RSA_PUBLIC_KEY_B64`
- `HMAC_SECRET_B64`
- `GEMINI_ENABLED=false` for local fallback generation, or `true` if you also set `GEMINI_API_KEY`
- `GEMINI_API_KEY` only when Gemini is enabled

Generate base64 values from your local keys with PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("backend\keys\private_key.pem"))
[Convert]::ToBase64String([IO.File]::ReadAllBytes("backend\keys\public_key.pem"))
[Convert]::ToBase64String([IO.File]::ReadAllBytes("backend\keys\hmac_secret.key"))
```

## Important persistence note

Vercel Functions do not provide durable local SQLite storage. The app uses `/tmp/data/provenance.db` on Vercel so the API can run, but records may disappear on cold starts or between serverless instances. For production, replace `ProvenanceStoreService` with a hosted database such as Vercel Postgres, Neon, Supabase, or another external DB.
