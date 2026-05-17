Task: Add a server time endpoint. Requirements: - GET 
/server-time - returns current server timestamp in 
ISO format - response example:
  {
    "timestamp": "2026-05-17T18:00:00.000Z"
  } - keep changes minimal
- add test if test setup already exists
