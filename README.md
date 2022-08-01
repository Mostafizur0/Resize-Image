# Resize-Image
PlurelSight Getting Started with Python 3 Concurrency Course

# Notes:
1. Never mix up I/O bound & CPU bound code in same method, because Python has different optimization for these 2 type of operations.
2. Thread Lifecycle: new -> ready <--> running (->) (blocked) -> terminated
3. During context switch if next thread is from the same process then only thread switching occurs but if the next thread is from a different process then process switch happens which is a costly operation. For this reason parallel processing using thread is preferred over using processes.
4. for synchronization, we can use threading.Lock()/threading.RLock()/threading.Semaphore()