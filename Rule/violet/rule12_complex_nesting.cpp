// 违反规则12：其它未列举的、更复杂的嵌套组合
// 违规形式：if-for-switch多层嵌套，层级混乱
#include <iostream>
using namespace std;

int main()
{
    int a = 10;
    int x = 2;
    for (int i = 0; i < 3; i++)
    {
        if (a > 5)
        {
            switch(x)
            {
                case 1:
                    a++;
                    break;
                case 2:
                    while (a < 20)
                    {
                        a++;
                    }
                    break;
            }
        }
    }
    return 0;
}
