/**
 * @jsx React.DOM
 */

var TextMap = React.createClass({
  loadStatusFromServer: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'text',
      success: function(data) {
        this.setState({data: data});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: ""};
  },
  componentDidMount: function() {
    this.loadStatusFromServer();
    setInterval(this.loadStatusFromServer, this.props.pollInterval);
  },
  render: function() {
    return (
      <div>{this.state.data}</div>
    );
  }
});

React.renderComponent(
  <TextMap url="map.txt" pollInterval={1000} />,
  document.getElementById('map')
);
