#!/bin/bash

# Script to publish distributed-observability-tools v0.1.1 to TestPyPI
# 
# Before running this script:
# 1. Make sure you have a TestPyPI account: https://test.pypi.org/account/register/
# 2. Generate an API token: https://test.pypi.org/manage/account/token/
# 3. Run this script and paste your API token when prompted

set -e

echo "=========================================="
echo "Publishing to TestPyPI - Version 0.1.1"
echo "=========================================="
echo ""

# Check if dist files exist
if [ ! -f "dist/distributed_observability_tools-0.1.1-py3-none-any.whl" ]; then
    echo "❌ Error: Wheel file not found!"
    echo "Please run: python -m build"
    exit 1
fi

if [ ! -f "dist/distributed_observability_tools-0.1.1.tar.gz" ]; then
    echo "❌ Error: Source distribution not found!"
    echo "Please run: python -m build"
    exit 1
fi

echo "✅ Found distribution files:"
ls -lh dist/distributed_observability_tools-0.1.1*
echo ""

# Verify package integrity
echo "🔍 Checking package integrity..."
twine check dist/distributed_observability_tools-0.1.1*

if [ $? -ne 0 ]; then
    echo "❌ Package check failed!"
    exit 1
fi

echo "✅ Package integrity check passed"
echo ""

# Upload to TestPyPI
echo "📦 Uploading to TestPyPI..."
echo ""
echo "⚠️  You will be prompted for your TestPyPI API token"
echo "    Username: __token__"
echo "    Password: Your TestPyPI API token (starts with 'pypi-')"
echo ""

twine upload --repository testpypi dist/distributed_observability_tools-0.1.1*

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Successfully published to TestPyPI!"
    echo "=========================================="
    echo ""
    echo "📦 Package: distributed-observability-tools"
    echo "🔖 Version: 0.1.1"
    echo "🔗 URL: https://test.pypi.org/project/distributed-observability-tools/0.1.1/"
    echo ""
    echo "🧪 Test installation:"
    echo "   pip install --index-url https://test.pypi.org/simple/ \\"
    echo "       --extra-index-url https://pypi.org/simple \\"
    echo "       distributed-observability-tools==0.1.1"
    echo ""
    echo "📝 What's new in v0.1.1:"
    echo "   - Configurable HTTP header capture in OpenTelemetry spans"
    echo "   - Wildcard pattern matching for headers (e.g., 'x-*')"
    echo "   - Automatic header redaction for sensitive data"
    echo "   - Enhanced FastAPIConfig and HTTPClientConfig"
    echo "   - Backward compatible with v0.1.0"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Upload failed!"
    echo "=========================================="
    echo ""
    echo "Common issues:"
    echo "1. Invalid API token - Generate a new one at https://test.pypi.org/manage/account/token/"
    echo "2. Version already exists - Bump version in pyproject.toml"
    echo "3. Network issues - Check your internet connection"
    echo ""
    exit 1
fi

