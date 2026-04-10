// 违反规则3：含有双分支结构的程序
// 违规形式：if-else单语句同行，且大括号位置错误
#include <iostream>
using namespace std;

int main()
{
    int a = 10;
    if (a > 5) { cout << "a>5" << endl; }
    else { cout << "a<=5" << endl; } // 多语句同行
    return 0;
}
