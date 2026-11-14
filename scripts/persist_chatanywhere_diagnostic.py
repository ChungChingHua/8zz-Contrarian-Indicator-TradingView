"""Persist the diagnostic audit using the existing narrow GitHub-only writer. MPL-2.0."""
from unittest.mock import patch
import persist_authorized_audit as persist
from diagnose_chatanywhere_403 import REPORT,SCOPE

if __name__=='__main__':
    with patch.object(persist,'REPORT',REPORT),patch.object(persist,'SCOPE',SCOPE):
        persist.main()
