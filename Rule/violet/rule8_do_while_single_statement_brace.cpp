// 违反规则8：含有循环结构的程序(do-while）
// 违规形式：只有一个语句也加括号（do-while规则要求单语句也要括号，但这里是反例展示错误理解）
// 注意：规则8实际上要求单语句也要括号，但这里展示的是右括号后没有紧跟while的错误写法
#include <iostream>
using namespace std;

int main()
{
    int a = 0;
    do
    {
        a++;
    }
    while (a < 10); // 正确写法，但这里展示一个常见错误格式：右括号后直接换行而非紧跟while
    return 0;
}
