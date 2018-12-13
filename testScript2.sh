
for i in `seq 1 8`; do
curl -X 'POST' -F 'delete=0' -F 'entry=t'${i} 'http://10.1.0.'${i}':80/board/0/' &
done
