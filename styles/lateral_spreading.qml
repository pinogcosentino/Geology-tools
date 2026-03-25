<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34" styleCategories="AllStyleCategories">

  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>

  <renderer-v2 type="categorizedSymbol"
               attr="formula"
               forceraster="0"
               symbollevels="0"
               enableorderby="0"
               referencescale="-1">

    <categories>
      <category value="Z0=(0&lt;IL≤2) and (2&lt;slope≤5)"
                label="Z0  |  0 &lt; IL ≤ 2  and  2 &lt; slope% ≤ 5"
                symbol="0" render="true" type="string"/>
      <category value="SZ=(0&lt;IL≤2) and (5&lt;slope≤15)"
                label="SZ  |  0 &lt; IL ≤ 2  and  5 &lt; slope% ≤ 15"
                symbol="1" render="true" type="string"/>
      <category value="SZ=(2&lt;IL≤5) and (2&lt;slope≤5)"
                label="SZ  |  2 &lt; IL ≤ 5  and  2 &lt; slope% ≤ 5"
                symbol="2" render="true" type="string"/>
      <category value="SZ=(5&lt;IL≤15) and (2&lt;slope≤5)"
                label="SZ  |  5 &lt; IL ≤ 15  and  2 &lt; slope% ≤ 5"
                symbol="3" render="true" type="string"/>
      <category value="RZ=(0&lt;IL≤2) and (slope>15)"
                label="RZ  |  0 &lt; IL ≤ 2  and  slope% > 15"
                symbol="4" render="true" type="string"/>
      <category value="RZ=(2&lt;IL≤5) and (slope>5)"
                label="RZ  |  2 &lt; IL ≤ 5  and  slope% > 5"
                symbol="5" render="true" type="string"/>
      <category value="RZ=(5&lt;IL≤15) and (slope>5)"
                label="RZ  |  5 &lt; IL ≤ 15  and  slope% > 5"
                symbol="6" render="true" type="string"/>
      <category value="RZ=(IL>15) and (slope>2)"
                label="RZ  |  IL > 15  and  slope% > 2"
                symbol="7" render="true" type="string"/>
    </categories>

    <symbols>

      <!-- 0 · Z0 – verde #27AE60 -->
      <symbol name="0" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="39,174,96,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="27,122,67,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 1 · SZ 0<IL≤2 – arancio chiaro -->
      <symbol name="1" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="253,195,98,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="180,100,10,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 2 · SZ 2<IL≤5 – arancio medio #E67E22 -->
      <symbol name="2" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="230,126,34,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="160,80,10,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 3 · SZ 5<IL≤15 – arancio scuro -->
      <symbol name="3" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="200,90,20,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="140,55,5,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 4 · RZ 0<IL≤2 – coral -->
      <symbol name="4" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="250,150,130,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="180,50,30,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 5 · RZ 2<IL≤5 – rosso medio #E74C3C -->
      <symbol name="5" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="231,76,60,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="150,30,20,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 6 · RZ 5<IL≤15 – rosso scuro #C0392B -->
      <symbol name="6" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="192,57,43,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="120,25,15,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

      <!-- 7 · RZ IL>15 – bordeaux -->
      <symbol name="7" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <data_defined_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></data_defined_properties>
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color"         type="QString" value="130,20,10,204"/>
            <Option name="joinstyle"     type="QString" value="miter"/>
            <Option name="offset"        type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit"   type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="80,5,5,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>

    </symbols>

    <source-symbol>
      <symbol name="0" type="fill" clip_to_extent="1" alpha="0.80" force_rhr="0">
        <layer class="SimpleFill" pass="0" locked="0" enabled="1">
          <Option type="Map">
            <Option name="color"         type="QString" value="164,113,88,200"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="style"         type="QString" value="solid"/>
          </Option>
        </layer>
      </symbol>
    </source-symbol>

    <rotation/>
    <sizescale/>
    <orderby/>
  </renderer-v2>

  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontFamily="Arial" fontSize="7" fontWeight="50"
                  textColor="40,40,40,255" namedStyle="Regular"
                  fieldName="formula" isExpression="0"
                  fontItalic="0" fontUnderline="0" fontStrikeout="0"
                  textOpacity="1" blendMode="0"
                  multilineHeight="1" useSubstitutions="0"
                  allowHtml="0" legendString="Aa"
                  previewBkgrdColor="255,255,255,255">
        <text-buffer bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,210"
                     bufferBlendMode="0" bufferJoinStyle="128" bufferOpacity="0.85"
                     bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0"
                     bufferNoFill="0"/>
        <text-mask maskEnabled="0" maskSize="0" maskSizeUnits="MM"
                   maskOpacity="1" maskJoinStyle="128"
                   maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskType="0"/>
        <background shapeDraw="0"/>
        <shadow shadowDraw="0"/>
        <dd_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></dd_properties>
        <substitutions/>
      </text-style>
      <text-format leftDirectionSymbol="&lt;" rightDirectionSymbol=">"
                   reverseDirectionSymbol="0" addDirectionSymbol="0"
                   placeDirectionSymbol="0" formatNumbers="0"
                   decimals="3" plusSign="0" wrapChar="" autoWrapLength="0"
                   useMaxLineLengthForAutoWrap="1" multilineAlign="3"/>
      <placement placement="1" centroidInside="1" centroidWhole="0"
                 overrunDistance="0" overrunDistanceUnit="MM"
                 overrunDistanceMapUnitScale="3x:0,0,0,0,0,0"
                 dist="0" distUnits="MM" distMapUnitScale="3x:0,0,0,0,0,0"
                 repeatDistance="0" repeatDistanceUnits="MM"
                 repeatDistanceMapUnitScale="3x:0,0,0,0,0,0"
                 offsetType="0" quadOffset="4" xOffset="0" yOffset="0"
                 offsetUnits="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 angleOffset="0" preserveRotation="1"
                 maxCurvedCharAngleIn="25" maxCurvedCharAngleOut="-25"
                 priority="5" fitInPolygonOnly="1"
                 geometryGenerator="" geometryGeneratorEnabled="0"
                 geometryGeneratorType="PointGeometry"
                 layerType="PolygonGeometry" polygonPlacementFlags="2"/>
      <rendering obstacle="1" obstacleFactor="1" obstacleType="1"
                 upsidedownLabels="0" maxNumLabels="2000"
                 minFeatureSize="10" limitNumLabels="0"
                 fontMinPixelSize="3" fontMaxPixelSize="10000"
                 displayAll="0" zIndex="0"
                 scaleVisibility="1" scaleMin="1" scaleMax="25000"
                 blendMode="0" mergeLines="0" drawLabels="1"/>
      <dd_properties><Option type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option></dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint"      type="QString" value="pole_of_inaccessibility"/>
          <Option name="blendMode"        type="int"     value="0"/>
          <Option name="ddProperties"     type="Map"><Option name="name" type="QString" value=""/><Option name="properties"/><Option name="type" type="QString" value="collection"/></Option>
          <Option name="drawToAllParts"   type="bool"    value="false"/>
          <Option name="enabled"          type="QString" value="0"/>
          <Option name="labelAnchorPoint" type="QString" value="point_on_exterior"/>
          <Option name="minLength"        type="double"  value="0"/>
          <Option name="minLengthUnit"    type="QString" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>

  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <customproperties>
    <Option type="Map">
      <Option name="embeddedWidgets/count" type="int" value="0"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend type="default-vector" showLabelLegend="0"/>
  <referencedLayers/>
  <fieldConfiguration/>
  <aliases/>
  <splitPolicies/>
  <defaults/>
  <constraints/>
  <constraintExpressions/>
  <expressionfields/>
  <attributeactions/>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns/>
  </attributetableconfig>
  <conditionalstyles><rowstyles/><fieldstyles/></conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"/>
  <editformconfig><widgets/></editformconfig>
  <previewExpression>"formula"</previewExpression>
  <mapTip enabled="1">&lt;b>Code:&lt;/b> [% "code" %]&lt;br/>&lt;b>Formula:&lt;/b> [% "formula" %]</mapTip>
  <layerGeometryType>2</layerGeometryType>

</qgis>
