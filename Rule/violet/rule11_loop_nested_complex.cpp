// 违反规则11：多种语句相互嵌套（续）- 循环嵌套
// 违规形式：for嵌套while，右大括号层级混乱
#include <iostream>
using namespace std;

int main()
{
    for (int i = 0; i < 3; i++)
    {
        int j = 0;
        while (j < 3)
        {
            cout << i << "," << j << endl;
            j++;
        }
    }
    return 0;
}
