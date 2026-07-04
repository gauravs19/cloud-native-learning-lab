package com.example.consumer;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

@Component
public class EventListener {

    @Value("${app.process-delay-ms}")
    private long delayMs;

    // The pod's hostname — in k8s this is the pod name, so you can SEE which pod got which partition.
    private final String pod = System.getenv().getOrDefault("HOSTNAME", "local");

    @KafkaListener(topics = "${app.topic}", groupId = "${spring.kafka.consumer.group-id}")
    public void onMessage(ConsumerRecord<String, String> record,
                          @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) throws InterruptedException {
        Thread.sleep(delayMs); // simulate work so lag is observable
        System.out.printf("[pod=%s] partition=%d offset=%d key=%s value=%s%n",
                pod, partition, record.offset(), record.key(), record.value());
    }
}
