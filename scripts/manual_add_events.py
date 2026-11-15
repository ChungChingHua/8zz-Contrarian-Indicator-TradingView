#!/usr/bin/env python3
"""Import verified Apify JSON, then optionally classify a bounded batch (MPL-2.0).

Usage: python scripts/manual_add_events.py --facebook facebook.json --threads threads.json
       python scripts/manual_add_events.py --classify-limit 2

Legacy plain-text imports lacked post IDs, author identity and media, so cannot
safely enter the social pipeline. Use the actor JSON export with provenance.
No keyword fallback is used. Existing historic events remain in the template.
"""
from social_pipeline import main

if __name__ == '__main__':
    main()
