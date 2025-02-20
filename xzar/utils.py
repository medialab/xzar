import sys
import platform


def acquire_cross_platform_stdout():
    # stdout need to be wrapped so that windows get a correct csv
    # stream output
    # powershell sometimes writes a UTF-16-LE BOM in the stdout
    # before one has any chance to reconfigure the stream as UTF-8
    # Reference: https://stackoverflow.com/questions/68487529/how-to-ensure-python-prints-utf-8-and-not-utf-16-le-when-piped-in-powershell
    if "windows" in platform.system().lower():
        # NOTE: this is where we can print warnings about using -o on Windows if required
        assert sys.__stdout__ is not None
        assert sys.__stderr__ is not None

        # we reconfigure the stdout to be UTF-8 on windows
        sys.__stdout__.reconfigure(encoding="utf-8")
        sys.__stderr__.reconfigure(encoding="utf-8")

        return open(
            sys.__stdout__.fileno(),
            mode=sys.__stdout__.mode,
            buffering=1,
            encoding=sys.__stdout__.encoding,
            errors=sys.__stdout__.errors,
            newline="",
            closefd=False,
        )

    return sys.stdout
