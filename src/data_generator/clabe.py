def clabe_check_digit(first_17: str) -> int:
    if len(first_17) != 17:
        raise ValueError('Input must be 17 numeric characters long')
    weights = (3,7,1)*6
    weighted_mod = 0
    for d, w in zip(first_17,weights):
        weighted_mod += (int(d)*w) % 10
    return (10-(weighted_mod % 10))%10

def validate_clabe(clabe: str) -> bool:
    if len(clabe) != 18:
        return False
    return clabe_check_digit(clabe[:17]) == int(clabe[17])

def generate_clabe(bank_code: str, plaza_code: str, account_number: str) -> str:
    if len(bank_code) != 3:
        raise ValueError('bank_code must be 3 numeric characters long')
    if len(plaza_code) != 3:
        raise ValueError('plaza_code must be 3 numeric characters long')
    if len(account_number) > 11:
        raise ValueError('account_number must be less than or equal to 11')

    account_number = account_number.zfill(11)
    clabe_base = bank_code + plaza_code + account_number
    return clabe_base+ str(clabe_check_digit(clabe_base))

print(generate_clabe("032","180","00011835971"))
#print(validate_clabe("032180000118359719"))
#print(validate_clabe("032180000118359710"))
#print(validate_clabe("0321800001183597a9"))