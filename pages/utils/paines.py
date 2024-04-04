import locale


def formatar_dinheiro(valor):
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    return 'R$ ' + locale.currency(valor, grouping=True, symbol=None)


def colorir_celula_valor(valor):
    if valor > 0:
        return 'background-color: rgba(144, 238, 144, 0.3)'
    else:
        return 'background-color: rgba(255, 160, 122, 0.3)'


def colorir_celula_investimento(tipo):
    if tipo in ('Aplicação RDB', 'Resgate RDB'):
        return 'background-color: rgba(255, 255, 0, 0.3)'
