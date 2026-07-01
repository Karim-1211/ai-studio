# AI Studio Professional v2.0.2 Quota Guard - Install Guide

This release reduces Gemini rate-limit problems and prevents repeated 3 Options requests from overwhelming a free-tier Gemini key.

No database migration is required. No Render environment variable changes are required.

## Install

Run the install script from the package folder and provide your project path.

## Validate

Run the validation script. It checks Python compilation and required JavaScript quota-guard files.

## After Deploy

1. Hard refresh with Ctrl + Shift + R.
2. Test Single Answer first.
3. Wait 1-2 minutes before testing 3 Options.
