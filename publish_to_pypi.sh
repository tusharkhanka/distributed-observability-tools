#!/bin/bash

# Script to publish distributed-observability-tools to Production PyPI
# 
# Prerequisites:
# 1. Successfully tested on TestPyPI
# 2. Create account at https://pypi.org/account/register/
# 3. Generate API token at https://pypi.org/manage/account/token/
# 4. Run this script and enter your token when prompted

set -e

echo "🚀 Publishing distributed-observability-tools to Production PyPI..."
echo ""
echo "⚠️  WARNING: This will publish to the PRODUCTION PyPI!"
echo "   Make sure you've tested on TestPyPI first."
echo ""

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Publication cancelled."
    exit 1
fi

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
echo "   Password: Your PyPI API token (starts with pypi-)"
echo ""
echo "📝 Get your token from: https://pypi.org/manage/account/token/"
echo ""

# Upload to PyPI
echo "🚀 Uploading to Production PyPI..."
twine upload dist/*

echo ""
echo "🎉 Publication successful!"
echo ""
echo "🔍 View your package at:"
echo "   https://pypi.org/project/distributed-observability-tools/"
echo ""
echo "📦 Install with:"
echo "   pip install distributed-observability-tools"
echo ""
echo "📋 Post-publication checklist:"
echo "   ✅ Verify package appears on PyPI"
echo "   ✅ Test installation: pip install distributed-observability-tools"
echo "   ✅ Test import: python -c 'import distributed_observability'"
echo "   ✅ Update documentation with installation instructions"
echo "   ✅ Create GitHub release tag: git tag v0.1.0 && git push origin v0.1.0"
