#!/bin/bash

cd "$(dirname "$0")"

if [ ! -f ids.txt ]; then
    lynx -listonly -nonumbers -dump "http://www.csic.es/centros-de-investigacion1?p_p_id=centres_WAR_centresportlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_centres_WAR_centresportlet_action=paginate&_centres_WAR_centresportlet_gsa_index=false&_centres_WAR_centresportlet_orderByCol=name&_centres_WAR_centresportlet_orderByType=asc&_centres_WAR_centresportlet_delta=999&typeId=1" | grep "http://www.csic.es/centros-de-investigacion1/-/centro/" | sed -e 's/.*\///' -e 's/\?.*//' | sort -n | uniq > ids.txt
    lynx -listonly -nonumbers -dump "http://www.csic.es/centros-de-investigacion1?p_p_id=centres_WAR_centresportlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_centres_WAR_centresportlet_action=paginate&_centres_WAR_centresportlet_gsa_index=false&_centres_WAR_centresportlet_orderByCol=name&_centres_WAR_centresportlet_orderByType=asc&_centres_WAR_centresportlet_delta=999&typeId=2" | grep "http://www.csic.es/centros-de-investigacion1/-/centro/" | sed -e 's/.*\///' -e 's/\?.*//' | sort -n | uniq >> ids.txt
fi

while IFS='' read -r i || [[ -n "$line" ]]; do
    URL="http://www.csic.es/centros-de-investigacion1/-/centro/$i"
    printf -v OUT "id_%06d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
    URL="http://www.csic.es/centros-de-investigacion1?p_p_id=centres_WAR_centresportlet&p_p_lifecycle=0&p_p_state=exclusive&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_centres_WAR_centresportlet_action=location&_centres_WAR_centresportlet_id=$i"
    printf -v OUT "mp_%06d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
    sleep 3
done < "ids.txt"

sed -e '/^\s*$/d' -e 's/\s\s*/ /g' -i *.html

