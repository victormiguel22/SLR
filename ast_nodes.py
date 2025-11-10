from dataclasses import dataclass
from typing import List, Optional, Union

@dataclass
class No:
    """Classe base para nós da AST"""
    pass

@dataclass
class Programa(No):
    declaracoes: List[No]

@dataclass
class DeclaracaoVariavel(No):
    tipo: str
    nome: str
    valor_inicial: Optional[No] = None

@dataclass
class DeclaracaoFuncao(No):
    tipo_retorno: str
    nome: str
    parametros: List[tuple] # [(tipo, nome), ...]
    corpo: List[No]

@dataclass
class Atribuicao(No):
    nome: str
    valor: No

@dataclass
class ExpressaoBinaria(No):
    esquerda: No
    operador: str
    direita: No

@dataclass
class ExpressaoUnaria(No):
    operador: str
    operando: No

@dataclass
class Numero(No):
    valor: Union[int, float]

@dataclass
class Identificador(No):
    nome: str

@dataclass
class String(No):
    valor: str

@dataclass
class Booleano(No):
    valor: bool

@dataclass
class ComandoEscreva(No):
    expressao: No

@dataclass
class ComandoLeia(No):
    variavel: str

@dataclass
class ComandoSe(No):
    condicao: No
    bloco_se: List[No]
    bloco_senao: Optional[List[No]] = None

@dataclass
class ChamadaFuncao(No):
    nome: str
    argumentos: List[No]

@dataclass
class Retorne(No):
    valor: Optional[No] = None
