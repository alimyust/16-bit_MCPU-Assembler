; Fibonacci sequence generator for the custom ISA
; Stores the first 10 Fibonacci values starting at memory[0]
; r0 = hard-wired zero register
; r1 = current Fibonacci value
; r2 = next Fibonacci value
; r3 = number of values to generate
; r4 = loop counter
; r5 = output memory pointer
; r6 = scratch / comparison / next value

start:
    ADDI r1, r0, 0
    ADDI r2, r0, 1
    ADDI r3, r0, 10
    ADDI r4, r0, 0
    ADDI r5, r0, 0

fib_loop:
    SUBS r6, r4, r3
    BRGE fib_done

    STR r1, [r5, 0]
    ADDI r5, r5, 1

    ADD r6, r1, r2
    ADD r1, r2, r0
    ADD r2, r6, r0
    ADDI r4, r4, 1

    BR fib_loop

fib_done:
    BR fib_done
