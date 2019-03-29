import os
import redis

r = redis.from_url("redis://h:p2683f9465e2fcbb6e728f84f905a3234994c14cc2be4e7bcff93c653b67a4480@ec2-35-168-215-149.compute-1.amazonaws.com:17159")
r.set('foo', 'bar')
value = r.get('foo')
print(value)