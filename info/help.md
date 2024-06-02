### Про папки
- В папке info:
  1. help.md - краткая справка
  2. lab3-task.md - вариант + задание
- В папке progs находится код программ.
- В папке source:
  1. inp - содержит входной файл для модели 
  2. machine_code - машинные коды, сгенерированные транслятором. 
  3. Модель процессора (machine, instruction_decoder, isa, ALU) и транслятор (translator.py).
- В папке tests:
  1. golden - шаблоны golden тестов
  2. test_golden.py - запуск golden тестов

### Запуск
1. Для запуска транслятора есть 2 опции:
   1. ```python translator.py <путь-до-программы>``` -  машкод появится в папке с исходным кодом программы.
   2. ```python translator.py -a``` - транслировать все программы. Машкод автоматически переместится в папку /source/machine_code/.
   3. Подробнее ```python translator.py -h```.
2. Для запуска модели есть 2 опции:
   1. ```python machine.py <входной файл, обычно source/inp/input.txt> <путь-до-машкода>``` - обычный запуск конкретного машкода на модели.
   2. ```python machine.py <входной файл, обычно source/inp/input.txt> -a``` - запуск всех машинных кодов по очереди.
   3. Подробнее ```python machine.py -h```.
3. Для запуска golden тестов ```poetry run pytest```
4. Для обновления golden тестов ```poetry run pytest . -v --update-goldens```
5. Для проверки ruff ```poetry run ruff format --check .```
6. Для форматирования ruff ```poetry run ruff format .```
   