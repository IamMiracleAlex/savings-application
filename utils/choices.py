########################################
#           TRANSACTION STATUS         #
########################################
class Transaction():
    SUBMITTED, PROCESSING, SUCCESS, FAILED, CANCELED = range(5)
    TRANSACTION_STATUS = (
        (SUBMITTED, 'SUBMITTED'),
        (PROCESSING, 'PROCESSING'),
        (CANCELED, 'CANCELED'),
        (SUCCESS, 'SUCCESS'),
        (FAILED, 'FAILED'),
    )

    QuickSave, AutoSave, ReferralBonus, TermDeposit, BankTransfer = range(5)
    DEPOSIT_TYPES = (
        (AutoSave, 'AutoSave'),
        (QuickSave, 'QuickSave'),
        (ReferralBonus, 'ReferralBonus'),
        (TermDeposit, 'TermDeposit'),
        (BankTransfer, 'BankTransfer'),
    )

    Deposit, Withdraw, Transfer, Payment, Interest = range(5)
    TRANSACTION_TYPES = (
        (Deposit, 'Deposit'),
        (Withdraw, 'Withdraw'),
        (Transfer, 'Transfer'),
        (Payment, 'Payment'),
        (Interest, 'Interest'),
    )