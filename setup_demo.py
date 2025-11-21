"""
Demo Mode Setup - Educational Roguelike Game
Creates sample questions without needing Claude API
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import pdf_manager, question_manager, db

print("🎮 Educational Roguelike - Demo Mode Setup")
print("=" * 60)

# Create a demo PDF entry
print("\n📄 Creating demo PDF entry...")
pdf_id = pdf_manager.add_pdf(
    filename="demo_python_basics.pdf",
    filepath="/demo/python_basics.pdf",
    title="Python Programming Basics (Demo)",
    num_pages=10,
    total_chars=5000
)
print(f"✅ Demo PDF created with ID: {pdf_id}")

# Mark as processed
pdf_manager.mark_processed(pdf_id)

# Sample questions about Python (you can change the topic)
demo_questions = [
    {
        'question_text': '¿Qué es Python?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Un lenguaje de programación de alto nivel',
        'options': [
            'Un lenguaje de programación de alto nivel',
            'Una serpiente venenosa',
            'Un framework de JavaScript',
            'Un sistema operativo'
        ],
        'explanation': 'Python es un lenguaje de programación interpretado de alto nivel, conocido por su sintaxis clara y legibilidad.',
        'topic': 'Introducción a Python',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Cuál es la extensión de archivo para scripts de Python?',
        'question_type': 'multiple_choice',
        'correct_answer': '.py',
        'options': ['.py', '.python', '.pt', '.script'],
        'explanation': 'Los archivos de Python usan la extensión .py',
        'topic': 'Fundamentos',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Python usa indentación para definir bloques de código?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'Python usa indentación (espacios o tabs) en lugar de llaves {} para definir bloques de código.',
        'topic': 'Sintaxis',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Qué imprime print("Hola" + "Mundo")?',
        'question_type': 'multiple_choice',
        'correct_answer': 'HolaMundo',
        'options': ['HolaMundo', 'Hola Mundo', 'Hola+Mundo', 'Error'],
        'explanation': 'El operador + concatena strings en Python sin espacios automáticos.',
        'topic': 'Strings',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Cuál es el tipo de dato de [1, 2, 3]?',
        'question_type': 'multiple_choice',
        'correct_answer': 'list',
        'options': ['list', 'tuple', 'dict', 'set'],
        'explanation': 'Los corchetes [] definen listas en Python, que son mutables y ordenadas.',
        'topic': 'Tipos de Datos',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Python es un lenguaje compilado?',
        'question_type': 'true_false',
        'correct_answer': 'false',
        'options': ['true', 'false'],
        'explanation': 'Python es un lenguaje interpretado, no compilado. El código se ejecuta línea por línea.',
        'topic': 'Fundamentos',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Qué hace la función len()?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Devuelve la longitud de un objeto',
        'options': [
            'Devuelve la longitud de un objeto',
            'Borra un elemento',
            'Convierte a minúsculas',
            'Crea una lista'
        ],
        'explanation': 'len() retorna el número de elementos en un objeto iterable como listas, strings, etc.',
        'topic': 'Funciones Built-in',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Cuál es el resultado de 10 // 3?',
        'question_type': 'multiple_choice',
        'correct_answer': '3',
        'options': ['3', '3.33', '3.0', 'Error'],
        'explanation': 'El operador // realiza división entera (floor division), retornando solo la parte entera.',
        'topic': 'Operadores',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Los diccionarios en Python son ordenados desde Python 3.7+?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'Desde Python 3.7, los diccionarios mantienen el orden de inserción.',
        'topic': 'Diccionarios',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Qué palabra clave se usa para definir una función?',
        'question_type': 'multiple_choice',
        'correct_answer': 'def',
        'options': ['def', 'function', 'func', 'define'],
        'explanation': 'La palabra clave "def" se usa para definir funciones en Python.',
        'topic': 'Funciones',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿range(5) genera números del 0 al 5 inclusive?',
        'question_type': 'true_false',
        'correct_answer': 'false',
        'options': ['true', 'false'],
        'explanation': 'range(5) genera números del 0 al 4. El límite superior es exclusivo.',
        'topic': 'Iteración',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Cuál es el operador de igualdad en Python?',
        'question_type': 'multiple_choice',
        'correct_answer': '==',
        'options': ['==', '=', '===', 'eq'],
        'explanation': '== compara valores, mientras que = asigna valores.',
        'topic': 'Operadores',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Las tuplas son mutables?',
        'question_type': 'true_false',
        'correct_answer': 'false',
        'options': ['true', 'false'],
        'explanation': 'Las tuplas son inmutables. Una vez creadas, no se pueden modificar.',
        'topic': 'Tipos de Datos',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Qué hace el método .append()?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Agrega un elemento al final de una lista',
        'options': [
            'Agrega un elemento al final de una lista',
            'Agrega un elemento al inicio',
            'Elimina el último elemento',
            'Ordena la lista'
        ],
        'explanation': '.append() añade un elemento al final de una lista.',
        'topic': 'Listas',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿None es un tipo de dato en Python?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'None es un tipo especial que representa la ausencia de valor.',
        'topic': 'Tipos de Datos',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Qué estructura de control se usa para repetir código?',
        'question_type': 'multiple_choice',
        'correct_answer': 'for o while',
        'options': ['for o while', 'if', 'def', 'return'],
        'explanation': 'Los bucles for y while permiten repetir bloques de código.',
        'topic': 'Control de Flujo',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Python distingue entre mayúsculas y minúsculas?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'Python es case-sensitive: "Variable" y "variable" son diferentes.',
        'topic': 'Fundamentos',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Cuál es el resultado de "Python"[0]?',
        'question_type': 'multiple_choice',
        'correct_answer': 'P',
        'options': ['P', 'Python', '0', 'Error'],
        'explanation': 'Los strings se pueden indexar como listas. El índice 0 retorna el primer carácter.',
        'topic': 'Strings',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Los sets permiten elementos duplicados?',
        'question_type': 'true_false',
        'correct_answer': 'false',
        'options': ['true', 'false'],
        'explanation': 'Los sets automáticamente eliminan duplicados, manteniendo solo valores únicos.',
        'topic': 'Tipos de Datos',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Qué hace la palabra clave "break"?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Termina el bucle actual',
        'options': [
            'Termina el bucle actual',
            'Pausa el programa',
            'Salta a la siguiente iteración',
            'Retorna un valor'
        ],
        'explanation': '"break" sale inmediatamente del bucle más cercano.',
        'topic': 'Control de Flujo',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Python requiere punto y coma al final de cada línea?',
        'question_type': 'true_false',
        'correct_answer': 'false',
        'options': ['true', 'false'],
        'explanation': 'Python no requiere punto y coma al final de las líneas (aunque es opcional).',
        'topic': 'Sintaxis',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Qué operador se usa para exponenciación?',
        'question_type': 'multiple_choice',
        'correct_answer': '**',
        'options': ['**', '^', 'pow', 'exp'],
        'explanation': 'El operador ** eleva un número a una potencia. Ejemplo: 2**3 = 8',
        'topic': 'Operadores',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Las variables en Python necesitan declaración de tipo?',
        'question_type': 'true_false',
        'correct_answer': 'false',
        'options': ['true', 'false'],
        'explanation': 'Python tiene tipado dinámico. No necesitas declarar el tipo de las variables.',
        'topic': 'Fundamentos',
        'difficulty': 'easy'
    },
    {
        'question_text': '¿Qué retorna la función input()?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Un string',
        'options': ['Un string', 'Un integer', 'Un float', 'Depende del input'],
        'explanation': 'input() siempre retorna un string, incluso si introduces números.',
        'topic': 'Input/Output',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Se puede usar "else" con bucles for/while?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'Python permite un bloque "else" después de bucles, que se ejecuta si el bucle termina normalmente.',
        'topic': 'Control de Flujo',
        'difficulty': 'hard'
    },
    {
        'question_text': '¿Qué hace el método .split()?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Divide un string en una lista',
        'options': [
            'Divide un string en una lista',
            'Une elementos de una lista',
            'Elimina espacios',
            'Convierte a mayúsculas'
        ],
        'explanation': '.split() divide un string en una lista de substrings basándose en un separador.',
        'topic': 'Strings',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Python soporta herencia múltiple?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'Python permite que una clase herede de múltiples clases padre.',
        'topic': 'POO',
        'difficulty': 'hard'
    },
    {
        'question_text': '¿Cuál es el valor de bool([]) (lista vacía)?',
        'question_type': 'multiple_choice',
        'correct_answer': 'False',
        'options': ['False', 'True', 'None', 'Error'],
        'explanation': 'Listas vacías, strings vacíos, 0, None evalúan a False en contexto booleano.',
        'topic': 'Tipos de Datos',
        'difficulty': 'hard'
    },
    {
        'question_text': '¿Los parámetros de función pueden tener valores por defecto?',
        'question_type': 'true_false',
        'correct_answer': 'true',
        'options': ['true', 'false'],
        'explanation': 'Python permite definir valores por defecto: def func(x=10):',
        'topic': 'Funciones',
        'difficulty': 'medium'
    },
    {
        'question_text': '¿Qué hace "continue" en un bucle?',
        'question_type': 'multiple_choice',
        'correct_answer': 'Salta a la siguiente iteración',
        'options': [
            'Salta a la siguiente iteración',
            'Termina el bucle',
            'Pausa el programa',
            'Retorna None'
        ],
        'explanation': '"continue" salta el resto del código en la iteración actual y continúa con la siguiente.',
        'topic': 'Control de Flujo',
        'difficulty': 'medium'
    }
]

print(f"\n📝 Insertando {len(demo_questions)} preguntas de ejemplo...")

# Insert questions
for i, q in enumerate(demo_questions, 1):
    question_manager.add_question(
        pdf_id=pdf_id,
        question_text=q['question_text'],
        question_type=q['question_type'],
        correct_answer=q['correct_answer'],
        options=q['options'],
        explanation=q['explanation'],
        topic=q['topic'],
        difficulty=q['difficulty']
    )
    if i % 5 == 0:
        print(f"  ✓ {i}/{len(demo_questions)} preguntas insertadas...")

print(f"\n✅ ¡Listo! {len(demo_questions)} preguntas insertadas exitosamente")
print(f"\n📊 Resumen:")
print(f"  - PDF Demo ID: {pdf_id}")
print(f"  - Total de preguntas: {len(demo_questions)}")
print(f"  - Preguntas fáciles: {sum(1 for q in demo_questions if q['difficulty'] == 'easy')}")
print(f"  - Preguntas medias: {sum(1 for q in demo_questions if q['difficulty'] == 'medium')}")
print(f"  - Preguntas difíciles: {sum(1 for q in demo_questions if q['difficulty'] == 'hard')}")

print("\n" + "=" * 60)
print("🎮 ¡Modo demo configurado!")
print("\nAhora puedes ejecutar el juego:")
print("  python app.py")
print("\nY jugar con el PDF de demostración sin necesidad de API Key.")
print("=" * 60)
