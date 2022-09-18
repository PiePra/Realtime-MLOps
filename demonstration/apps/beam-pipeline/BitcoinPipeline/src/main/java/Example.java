import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.kafka.KafkaIO;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.Values;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.LongDeserializer;

import java.util.Arrays;
import java.util.List;

public class Example {
    public static void main(String[] args) {
        PipelineOptions pipelineOptions = PipelineOptionsFactory.create();
        Pipeline pipeline = Pipeline.create(pipelineOptions);

        final List<String> input = Arrays.asList("First", "Second", "Third", "last");
        pipeline.apply(
                        KafkaIO.<Long, String>read()
                                .withBootstrapServers("streaming-system-kafka-0.kafka.svc.cluster.local:9094")
                                .withTopic("knative-broker-default-btc")
                                .withKeyDeserializer(LongDeserializer.class)
                                .withValueDeserializer(StringDeserializer.class)
                                .withMaxNumRecords(1)
                                .withoutMetadata()

                ).apply(Values.<String>create())
                .apply(TextIO.write().to("wordcounts"));


        pipeline.run().waitUntilFinish();
    }
}
