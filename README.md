# Disney Touch Point
Using NFC technology, I want to create the Touch Point Disney offers at its entrances for my own personal use at home.   

To include upon read:
- Lights
- Sounds

# Wiring
### [RFID-RC522]([url](https://www.aliexpress.us/item/3256807702682933.html?src=google&pdp_npi=4%40dis%21USD%211.93%211.83%21%21%21%21%21%40%2112000042733086095%21ppc%21%21%21&src=google&albch=shopping&acnt=708-803-3821&isdl=y&slnk=&plac=&mtctp=&albbt=Google_7_shopping&aff_platform=google&aff_short_key=UneMJZVf&gclsrc=aw.ds&albagn=888888&ds_e_adid=&ds_e_matchtype=&ds_e_device=c&ds_e_network=x&ds_e_product_group_id=&ds_e_product_id=en3256807702682933&ds_e_product_merchant_id=5361118735&ds_e_product_country=US&ds_e_product_language=en&ds_e_product_channel=online&ds_e_product_store_id=&ds_url_v=2&albcp=19108282527&albag=&isSmbAutoCall=false&needSmbHouyi=false&gad_source=4&gad_campaignid=19108284222&gbraid=0AAAAAD6I-hG8uvCz8eJx-4KrPtgV7_Q_m&gclid=CjwKCAiA3L_JBhAlEiwAlcWO5zNo3PJEIUwrV0wFFY6Pn6aLm5L0AHmTl1ij-rV7HRp9U0M2BvWzFxoC5BoQAvD_BwE&gatewayAdapt=glo2usa))
| RC522 Pin | Pi Pin              | Notes                        |
| --------- | ------------------- | ---------------------------- |
| SDA / NSS | GPIO8 (CE0, Pin 24) |                              |
| SCK       | GPIO11 (Pin 23)     | Clock                        |
| MOSI      | GPIO10 (Pin 19)     | Data to RC522                |
| MISO      | GPIO9  (Pin 21)     | Data from RC522              |
| RST       | GPIO25 (Pin 22)     | Reset — must match your code |
| 3.3V      | Pin 1 or 17         | Only 3.3V!                   |
| GND       | Pin 6               | Ground                       |

### ws2812b
|ws2812b Pin | Pi Pin   |
|------------|----------|
|5v          |5v        |
|DIN         |GPIO18    |
|GND         |GND       |


To run:
```bash
sudo ~/touch_point/venv/bin/python touch_point.py
```
# [3D Print of Reader](https://www.thingiverse.com/thing:4549215)
