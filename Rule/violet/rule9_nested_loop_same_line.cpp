// 违反规则9：含有循环相互嵌套的程序
// 违规形式：嵌套循环右大括号不缩进，层级混乱
#include <iostream>
using namespace std;

int main()
{
    for (int i = 0; i < 3; i++)
    {
        for (int j = 0; j < 3; j++)
        {
            cout << i << "," << j << endl;
        }
    }
    return 0;
}
