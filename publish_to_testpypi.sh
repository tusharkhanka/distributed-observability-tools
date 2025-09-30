#!/bin/bash

# Script to publish distributed-observability-tools to TestPyPI
# 
# Prerequisites:
# 1. Create account at https://test.pypi.org/account/register/
# 2. Generate API token at https://test.pypi.org/manage/account/token/
# 3. Run this script and enter your token when prompted

set -e

echo "🚀 Publishing distributed-observability-tools to TestPyPI..."
echo ""
echo "📋 Pre-flight checks:"

# Activate virtual environment
source venv/bin/activate

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo "❌ twine not found. Installing..."
    pip install twine
fi

# Verify package
echo "✅ Checking package integrity..."
twine check dist/*

echo ""
echo "📦 Package contents:"
ls -la dist/

echo ""
echo "🔐 Authentication required:"
echo "   Username: __token__"
echo "   Password: Your TestPyPI API token (starts with pypi-)"
echo ""
echo "📝 Get your token from: https://test.pypi.org/manage/account/token/"
echo ""

# Upload to TestPyPI
echo "🚀 Uploading to TestPyPI..."
twine upload --repository testpypi dist/*

echo ""
echo "✅ Upload complete!"
echo ""
echo "🔍 View your package at:"
echo "   https://test.pypi.org/project/distributed-observability-tools/"
echo ""
echo "🧪 Test installation:"
echo "   pip install --index-url https://test.pypi.org/simple/ distributed-observability-tools"
echo ""
echo "📋 Next steps:"
echo "   1. Test the package installation and functionality"
echo "   2. If everything works, publish to production PyPI using publish_to_pypi.sh"
