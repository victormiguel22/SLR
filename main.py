from AnalisadorLexico import AnalisadorLexico
from AnalisadorSLR import AnalisadorSLR

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
    
    # Fase 2: Análise Sintática
    print("\n[FASE 2] Análise Sintática...")
    parser = AnalisadorSLR(tokens)
    success = parser.analisar()
    
    print("\nResultado da análise sintática:")
    parser.imprimir_erros()
    
    if parser.erros:
        print(f"✗ Erros sintáticos encontrados: {len(parser.erros)}")
        return None
    
    print("✓ Análise sintática concluída com sucesso!")
    
    return success

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
    
