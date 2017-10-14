== FAILED: BUY ==

{'error': {'toadd': 'The time to extend the license is invalid!'}}

== SUCCESS: BUY ==

{'lid': 74104, 'added': '1M', 'license': '93227-48449-56766-92991-79108', 'ip': '10.0.0.1', 'error': None, 'autorenew': 'NO', 'rate': 0.6, 'time': 1350918883, 'action': 'new', 'bal': 187.79999999999998, 'amt': 0.6, 'actid': 285858}
{"content_length": 1, "content": [{"lid": "74104", "added": "1M", "license": "93227-48449-56766-92991-79108", "ip": "10.0.0.1", "error": null, "autorenew": "NO", "rate": 0.6, "time": 1351108751, "action": "renew", "bal": 214.79999999999998, "amt": 0.6, "actid": 288170}], "message_type": "response", "response_type": "success"}
== SUCCESS: REFUND ==

{'lid': '74104', 'added': '-1M', 'license': '93227-48449-56766-92991-79108', 'error': None, 'cancelled_autorenewal': 1, 'rate': '0.60', 'time': 1350920059, 'action': 'refund', 'bal': 197.4, 'amt': -0.6, 'actid': 285858}

NOTE: In web panel, license is marked as expiring 22/10/2012, i.e. the day it was bought. Despite 'added': '-1M' entire time seems to have been refunded.

== FAILED: ALREADY REFUNDED ==
( WebClient calls: /noc?nocname=company&nocpass=LB7dqB9s0MJWJ1v3&ca=refund&actid=285858 )
{'error': {'already_refunded': 'This transaction has already been refunded to you.'}}


