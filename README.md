# ml-livestream-workflow

Scripts for NAB to do progressive tagging with live2vod and continual indexing

## Setup
```
1. conda create -n env python=3.10
2. conda activate env
3. pip install -e .
4. git clone git@github.com:eluv-io/elv-live-js.git -b l2v_tags
5. cd elv-live-js && npm install
```

## Configs
```
Set `configs/config.json` and `configs/config-search.json` with private key.
```

## Index watcher
```
python maintain_index.py --config configs/config-search.json --vod iq__4CahcfRQo7CvnbXLHpV5ZTxHd6Ji --index iq__32LqQRXfVtmeyA8Yi1fAMGbjcu7N
```

### To trigger rebuild immediately 
```
python maintain_index.py --config configs/config-search.json --vod iq__4CahcfRQo7CvnbXLHpV5ZTxHd6Ji --index iq__32LqQRXfVtmeyA8Yi1fAMGbjcu7N --right_away
```

## Maintain Live2Vod
```
1. export PRIVATE_KEY=...
2. python maintain_live2vod.py --config configs/config.json --livestream iq__4SxKRQ1pHojYrZKL14tD3Wm95uZY --vod iq__4CahcfRQo7CvnbXLHpV5ZTxHd6Ji
```

## Tag livestream
```
1. python tag_livestream.py --config configs/config.json --livestream iq__4SxKRQ1pHojYrZKL14tD3Wm95uZY
```

### External tags
I've included the relevant external tags file already trimmed, but if the source video changes we can run

```
python trim_source.py --input_file original.json --output_file trimmed.json --new_start_time 1644000
```

To get trimmed file. 

The tag script is hardcoded to use rugbyviz_master.json as the source file and will trim this based on how progressed the livestream is. 

### Full flow
1. Create a fresh livestream or deactivate and reactivate an existing one
2. Start livestream
3. Start the three watcher scripts: `tag_livestream.py`, `maintain_live2vod.py`, `maintain_index.py`

To start over, deactivate and reactivate the livestream (assuming there is a script running which is constantly publishing the source video which there is). The tags, index, vod will be maintained until the livestream reaches the end. 
If a new period starts, the scripts will pause until the livestream reboots. 