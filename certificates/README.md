# GePG Certificates

Place the PKCS#12 certificate files here (they are gitignored — never committed):

- `private.pfx` — TGC private key for signing outbound requests
- `public.pfx` — GePG public certificate

Then in `.env`:

```
GEPG_PRIVATE_KEY_PATH=certificates/private.pfx
GEPG_PUBLIC_CERT_PATH=certificates/public.pfx
GEPG_CERTIFICATE_PASSWORD=<the .pfx password>
GEPG_USE_DIGITAL_SIGNATURE=True
```

Leaving `GEPG_PRIVATE_KEY_PATH` / `GEPG_PUBLIC_CERT_PATH` blank falls back to the
default paths above. Signing is skipped while `GEPG_USE_DIGITAL_SIGNATURE=False`.
