from factorypulse.agent.tools import *

print (get_status("M01","2026-10-12T09:04:03Z"))

print(50*"-")
print(get_history("M01","2026-10-12T09:04:00Z","2026-10-12T09:04:03Z"))