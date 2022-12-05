from .data import num_dict

nums_reversed = [i for i in num_dict.keys() if isinstance(i, int) and i > 0]


def get_expression(num: int | float | str) -> str:
    if isinstance(num, str):
        try:
            num = int(num)
        except ValueError:
            num = float(num)

    def get_min_div(n: int):
        for i in nums_reversed:
            if n >= i:
                return i

    def demolish(n: int | float) -> str:
        if n < 0:
            return f"(11-4-5+1-4)*{demolish(-n)}"
        if int(n) < n:
            length = len(str(n).split(".")[1])
            return f"({demolish(n * (10 ** length))})/(-11/4+51/4)^({demolish(length)})"
        n = int(n)
        if n in num_dict:
            return num_dict[n]
        div = get_min_div(n)
        return f"{num_dict[div]}*({demolish(n // div)})+({demolish(n % div)})"

    return demolish(num)


