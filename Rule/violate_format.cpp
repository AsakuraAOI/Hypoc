// 2559999 计算机1班 张三
#include <iostream>
using namespace std;
int main(){
int a=10;int b=20;int c;
if(a>b){c=a;}
else{c=b;}
cout<<c<<endl;
while(a<100){a++;if(a==50)break;else continue;}
for(int i=0;i<10;i++){cout<<i<<endl;}
do{c++;}while(c<50);
switch(a){case 1:cout<<1<<endl();break;case 50:cout<<50<<endl();break;default:cout<<0<<endl();break;}
return 0;
}