// 违反规则2：含有单分支结构的程序
// 违规形式：单语句分支与if同行
#include <iostream>
using namespace std;

int main()
{
    int a = 10;
    if (a > 5) cout << "a>5" << endl; // 单语句与if同行
    return 0;
}
