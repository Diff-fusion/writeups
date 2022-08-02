handle SIGSEGV pass nostop noprint
handle SIGILL nostop noprint

# watch *0x84747f8

b *0x080b0bd9 if *0x84747f8 == 1
commands 1
output $eax
quit
end

run
quit
