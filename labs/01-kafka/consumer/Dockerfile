# ---- build stage ----
FROM gradle:8.10-jdk21 AS build
WORKDIR /app
COPY settings.gradle build.gradle ./
RUN gradle dependencies --no-daemon > /dev/null 2>&1 || true   # cache deps in their own layer
COPY src ./src
RUN gradle bootJar --no-daemon

# ---- run stage ----
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/build/libs/consumer-1.0.0.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
