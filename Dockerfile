FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY scarfolder/ ./scarfolder/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .


# ---------------------------------------------------------------------------
# Final image
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# Non-root user for safer container execution
RUN useradd --create-home --no-log-init --shell /bin/bash scarfolder

# Copy installed package from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/scarfolder /usr/local/bin/scarfolder

# /workspace is the conventional mount point.
# Setting it on PYTHONPATH means any .py file or package placed there is
# importable by dotted path in YAML configs without any extra configuration.
ENV PYTHONPATH=/workspace

WORKDIR /workspace

USER scarfolder

ENTRYPOINT ["scarfolder"]
CMD ["--help"]
