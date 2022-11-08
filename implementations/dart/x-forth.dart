import "dart:io" show stdout;

const src = '2 3 + show drop 10 dup .s + .';

main() {
    final tokens = tokenize(src);
    print('** TOKENS **\n${tokens}');
    
    print('\n** INTERPRET **');
    try {
      interpret(tokens);
    } catch(e){
      print(e);
    }
}

const STACK_CAPACITY = 1024;
final stack = List<Value>.generate(STACK_CAPACITY, (_)=>Value());
var stack_top = -1;

const operators = [
  // math
  '+',
  '-',
  '*',
  '/',
  // logic
  '<',
  '>',
  '==',
  '!=',
];

final func_table = {
  '.'  : stack_print_top,
  '.s' : stack_display,
  'drop': stack_drop,
  'dup': stack_dup,
  'show' : (){ stack_print_top(consume: false); },
};

final words = [
  ...operators,
  // builtins
  ...func_table.keys,
];

enum ValueType {
    Undefined,
    number,
}

class Value {
    ValueType type; 
    dynamic value;
    Value({this.type=ValueType.Undefined,this.value=null});
}

error_stack_underflow(word)=> throw 'ERROR: ${word}: Stack underflow';

stack_print_top({consume=true}) {
  if(stack_top < 0) error_stack_underflow('.');
  final val = stack[stack_top];
  if(consume)
    stack_top--;
  print(val.value);
}

stack_display(){
    final count = stack_top + 1; 
     
    stdout.write('<${count}> ');
    if (count >= 1){
        for(var i = 0; i < count; i++) {
            final value = stack[i];
            if(value.value == null) {
                stdout.write('NULL ');
            } else {
                stdout.write('${value.value} ');
            }
        }
    }
    stdout.write('ok\n');
}

stack_drop(){
  if (stack_top < 0) error_stack_underflow('drop');
  stack_top--;
}

stack_dup() {
  if (stack_top < 0) error_stack_underflow('dup');

  final val = stack[stack_top++];
  stack[stack_top].type = val.type;
  stack[stack_top].value = val.value;
}

interpret(tokens){
    tokens.forEach((token){
        // numbers
        if (double.tryParse(token) != null ){
            final number = double.tryParse(token);
            stack_top++;
            stack[stack_top].type = ValueType.number;
            stack[stack_top].value = number;
        // words
        } else if (words.contains(token)){
          // operator
          if (operators.contains(token)){
            // all current operators are binary, requiring two arguments
            if (stack_top < 1) error_stack_underflow(token);
            final b = stack[stack_top--];
            final a = stack[stack_top--];

            var result;
            if(token == '+')        result = a.value + b.value;
            else if(token == '-')   result = a.value - b.value;
            else if(token == '*')   result = a.value * b.value;
            else if(token == '/')   result = a.value / b.value;
            else if(token == '<')   result = a.value < b.value;
            else if(token == '>')   result = a.value > b.value? 1.0 : 0.0;
            else if(token == '==')  result = a.value == b.value? 1.0 : 0.0;
            else if(token == '!=')  result = a.value != b.value? 1.0 : 0.0;

            // assign the value
            stack[++stack_top].value=result;
            stack[stack_top].type=ValueType.number;
          // function
          } else {
            // lookup function in func_table
            func_table[token]!();
          }
          // function
        // Undefined
        } else {
            throw "ERROR: Undefined Token ${token}";
        } 
    });
}

tokenize(src){
    final tokens = [];
    var token = '';
    src.split('').asMap().forEach((i, c){
        if(is_whitespace(c)) {
            if(token.length > 0)
                tokens.add(token);
            token = '';
        // TODO strings
        } else {
            token += c;
            if(i >= src.length-1)
                tokens.add(token);
        }
    });
    return tokens;
}

is_whitespace(c){
    return c == ' ' || c == '\n' || c == '\r' || c == '\t';
}
