# Resize-Image
PlurelSight Getting Started with Python 3 Concurrency Course

# Notes:
1. Never mix up I/O bound & CPU bound code in same method, because Python has different optimization for these 2 type of operations.
2. Python threads are neither thread safe & not truly concurrent. As python uses Global Interpreter Lock (GIL) which blocks multiple thread run concurrently. So only use python threads for I/O bound operation as GIL is released from thread & the thread is blocked at that time.
3. Python shares single core between multiple threads by interrupting threads in a regular interval (like JS)
4. Currently only Jython & Iron-python are free from this limitation as Java & C# supports concurrent threads execution
5. Process do not share memory with other process normally. To share must go through special procedure
6. There is one GIL for each process. So to run concurrently we need to create multiple copy of a process
7. For multiprocessing new process must be inside the if __name__ = '__main__' block, otherwise unlimited process will be created & the program will crash
8. Daemon process can not create child process
9. Beware of using Process.terminate() as it will result in inconsistent result