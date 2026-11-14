"""GitHub-only sanitized quality audit writer, no AI secret access. MPL-2.0."""
from unittest.mock import patch
import persist_authorized_audit as p
from authorized_quality_test import REPORT,SCOPE
if __name__=='__main__':
    with patch.object(p,'REPORT',REPORT),patch.object(p,'SCOPE',SCOPE):p.main()
