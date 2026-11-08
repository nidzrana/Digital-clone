# My study notes: Operating Systems

## Why I like Operating Systems
Operating Systems is my favourite subject so far. I find it fun and interesting, and what I enjoy the most are the algorithms, especially the Banker's algorithm and Round Robin scheduling.

## Round Robin scheduling (my notes)
Round Robin is a CPU scheduling algorithm made for time-sharing systems. Every process gets a fixed slice of CPU time called the time quantum. When a process uses up its quantum and is not finished, it goes to the back of the ready queue and the next process gets its turn. This makes it fair, because no process waits forever.
The choice of quantum matters. If the quantum is too small, the CPU wastes a lot of time on context switches. If it is too large, Round Robin starts behaving like First Come First Served.

## Banker's algorithm (my notes)
The Banker's algorithm is used to avoid deadlock. It is called that because it works like a bank that never lends out more money than it can safely get back.
Before granting a resource request, the system checks whether it would still be in a safe state. A safe state means there is some order in which all processes can finish with the resources available. The algorithm keeps track of the Available resources, each process's Max demand and its current Allocation. The remaining Need is Max minus Allocation. If granting the request leaves the system safe, the request is approved. If not, the process has to wait.

## Why these two algorithms
I like them because they are logical and step by step. You can work through an example on paper and see exactly why a decision was made. That is why OS feels interesting to me and not just theory.
