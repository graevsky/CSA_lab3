: read_input
    1 0 do
        inp
        dup
        if
            dec_i
            store
        then
    loop
;

: print_output
    1 0 do
        load
        dup
        if
            dec_i
            out
        then
    loop
;


: greet
    cr
    ."Hello, what is your name?"
    cr
    read_input
    cr
    ."Hello, "
    print_output
;

greet