# Sample Insurance Documents

This directory contains sample insurance documents that the RAG pipeline uses to answer user queries.

## How to Add Documents

1. Place your insurance-related documents (`.txt`, `.md`, or `.pdf` text) in this directory
2. The RAG pipeline will automatically load and process them
3. Documents should contain relevant insurance information

## Sample Documents Included

The RAG pipeline comes with sample insurance data including:
- Insurance coverage information
- Policy details
- Claim procedures
- Company information

## Document Format

For best results, keep documents organized and focused on specific topics:

```
coverage_plans.txt
health_insurance.txt
life_insurance.txt
claims_process.txt
faqs.txt
```

## Notes

- Each file is split into chunks for better retrieval
- Larger documents are automatically split into manageable pieces
- The embedding model will index all documents on startup
- Updates require restarting the backend service
