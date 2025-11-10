from AnalisadorLexico import AnalisadorLexico
from AnalisadorSLR import AnalisadorSLR
from ast_nodes import *

def compilar(codigo_fonte: str, mostrar_tokens: bool = True):
    """Executa análise léxica e sintática"""
    print("\n" + "="*70)
    print("COMPILADOR - ANÁLISE LÉXICA E SINTÁTICA")
    print("="*70)
    
    # Fase 1: Análise Léxica
    print("\n[FASE 1] Análise Léxica...")
    lexer = AnalisadorLexico(codigo_fonte)
    tokens = lexer.analisar()
    
    print(f"✓ Total de tokens: {len(tokens) - 1}")
    
    if mostrar_tokens:
        print("\nTokens encontrados:")
        lexer.imprimir_tokens()
    
    if lexer.erros:
        print(f"✗ Erros léxicos encontrados: {len(lexer.erros)}")
        print("\nErros léxicos:")
        lexer.imprimir_erros()
        return None
    
    # Fase 2: Análise Sintática SLR
    print("\n[FASE 2] Análise Sintática SLR...")
    parser = AnalisadorSLR(tokens)
    ast = parser.analisar()
    
    print("\nResultado da análise SLR:")
    parser.imprimir_erros()
    
    if parser.erros:
        print(f"✗ Erros sintáticos encontrados: {len(parser.erros)}")
        return None
    
    print("✓ Análise Sintática SLR concluída com sucesso!")
    
    return ast

# ==================== EXEMPLOS DE TESTE ====================

if __name__ == "__main__":
    
    print("\n### EXEMPLO 1: Declarações e Atribuições ###")
    codigo1 = """
    inicio
        inteiro x := 10
        flutuante y := 3.14
        x := x + 5
        y := y * 2
    fim
    """
    compilar(codigo1)
    
    print("\n\n### EXEMPLO 2: Expressões Numéricas ###")
    codigo2 = """
    inicio
        inteiro resultado := (10 + 5) * 3 - 8 / 2
        flutuante calc := -5 + 10 * 2
    fim
    """
    compilar(codigo2)
    
    print("\n\n### EXEMPLO 3: Comando SE ###")
    codigo3 = """
    inicio
        inteiro idade := 25
        se idade >= 18 inicio
            escreva("Maior de idade")
        fim senao inicio
            escreva("Menor de idade")
        fim
    fim
    """
    compilar(codigo3)
    
    print("\n\n### EXEMPLO 4: Leitura e Escrita ###")
    codigo4 = """
    inicio
        inteiro numero
        cadeia nome := "João"
        
        leia(numero)
        escreva(nome)
        escreva(numero * 2)
    fim
    """
    compilar(codigo4)
    
    print("\n\n### EXEMPLO 5: Declaração de Função ###")
    codigo5 = """
    funcao inteiro soma(inteiro a, inteiro b) inicio
        inteiro resultado := a + b
        retorne resultado
    fim
    
    inicio
        inteiro x := 10
        inteiro y := 20
        inteiro z := soma(x, y)
        escreva(z)
    fim
    """
    compilar(codigo5)
    
    print("\n\n### EXEMPLO 6: Programa Completo ###")
    codigo6 = """
    funcao inteiro fatorial(inteiro n) inicio
        se n <= 1 inicio
            retorne 1
        fim senao inicio
            retorne n * fatorial(n - 1)
        fim
    fim
    
    inicio
        inteiro numero := 5
        inteiro fat := fatorial(numero)
        escreva(fat)
    fim
    """
    compilar(codigo6)
