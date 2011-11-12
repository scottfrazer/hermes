for file in *
do
  rm $file/first.json $file/follow.json $file/conflicts $file/conflicts.json 2>/dev/null
done
