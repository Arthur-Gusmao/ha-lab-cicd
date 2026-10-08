# Contributing

Open an issue describing a bug or improvement, or submit a focused pull request
targeting `master`. Explain the behavior before and after the change and how it
was validated.

Run the controller tests and build the application before submitting:

```bash
python3 -m unittest discover -s deploy -p 'test_*.py' -v
podman build -f Containerfile -t localhost/ha-webapp:local .
```

Changes merged into master may automatically deploy to the maintainer's lab.
Deployment-controller changes require separate local review and reinstallation.
Never submit secrets, private keys, personal environment files, or unreviewed
infrastructure exports. Keep project documentation in English.

This project is MIT-licensed; contributions are submitted under the same license.
