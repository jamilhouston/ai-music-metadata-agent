# Replit setup

This project runs as a Streamlit app.

## Run

The configured workflow starts:

```text
streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

The app uses the `OPENAI_API_KEY` and `APP_ACCESS_CODE` Replit Secrets. The first enables AI analysis; the second protects the private tester preview.