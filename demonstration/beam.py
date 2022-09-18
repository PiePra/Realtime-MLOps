import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from more_itertools import first
from apache_beam.io.kafka import ReadFromKafka

class AddTimestampDoFn(beam.DoFn):
  def process(self, element):
    timestamp = element["timestamp"]
    element = (element["key"], element["price"])
    # TimestampedValue.
    yield beam.transforms.window.TimestampedValue(element, timestamp)

_marker = object()
def last(iterable, default=_marker):
    from sys import hexversion
    from collections import deque
    from collections.abc import Sequence

    try:
        if isinstance(iterable, Sequence):
            return iterable[-1]
        # Work around https://bugs.python.org/issue38525
        elif hasattr(iterable, '__reversed__') and (hexversion != 0x030800F0):
            return next(reversed(iterable))
        else:
            return deque(iterable, maxlen=1)[-1]
    except (IndexError, TypeError, StopIteration):
        if default is _marker:
            raise ValueError(
                'last() was called on an empty iterable, and no default was '
                'provided.'
            )
        return default

beam_options = PipelineOptions()
with beam.Pipeline() as p:
    data =  p | 'Read Stream' >> ReadFromKafka(consumer_config={'bootstrap.servers': '10.89.0.200:9092'},
            topics=["knative-broker-default-btc"])
    timestamped_data = data | 'To time' >> beam.ParDo(AddTimestampDoFn())
    windowed_data = timestamped_data | 'To windows' >> beam.WindowInto(beam.window.Sessions(24 * 60 * 60))
    grouped_data = windowed_data | 'Group' >> beam.GroupByKey() 
    high = windowed_data | 'High' >> beam.CombineGlobally(min).without_defaults()  | 'Print high' >> beam.FlatMap(print)
    low = windowed_data | 'Low' >> beam.CombineGlobally(max).without_defaults() | 'Print low' >> beam.FlatMap(print)
    open = windowed_data | 'Open' >> beam.CombineGlobally(first).without_defaults() | 'Print open' >> beam.FlatMap(print)
    close = windowed_data | 'Close' >> beam.CombineGlobally(last).without_defaults() | 'Print close' >> beam.FlatMap(print)



#        ([
#        {"key": "btc", "price":19976.07,"timestamp":1662057603},
#        {"key": "btc","price":19977.07,"timestamp":1662056503.234},
#        {"key": "btc","price":19978.07,"timestamp":1662057503.234},
#        {"key": "btc","price":19979.07,"timestamp":1662058503.234},
#        {"key": "btc","price":19977.07,"timestamp":1662055950.234},
#        {"key": "btc","price":19975.07,"timestamp":1662056003.234}
#        ])    